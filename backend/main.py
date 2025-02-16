from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from typing import List, Optional
import uvicorn

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/employee_hierarchy.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database model
class EmployeeDB(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    title = Column(String)
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    
    # Define relationship for subordinates
    subordinates = relationship("EmployeeDB", 
                               backref="manager",
                               remote_side=[id])

# Create the database tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class EmployeeBase(BaseModel):
    name: str
    title: str
    manager_id: Optional[int] = None

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    id: int
    
    class Config:
        orm_mode = True

class EmployeeTree(Employee):
    subordinates: List["EmployeeTree"] = []

    class Config:
        orm_mode = True

# Resolve forward reference for EmployeeTree
EmployeeTree.update_forward_refs()

class EmployeeUpdate(BaseModel):
    employee_id: int
    manager_id: Optional[int] = None

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize FastAPI app
app = FastAPI(title="Tech Startup Employee Hierarchy API")

# Function to check for cycles in the hierarchy
def has_cycle(db: Session, employee_id: int, new_manager_id: int) -> bool:
    if employee_id == new_manager_id:
        return True
    
    # Check if the new manager is a subordinate of the employee
    current_manager_id = new_manager_id
    visited = set([employee_id])
    
    while current_manager_id is not None:
        if current_manager_id in visited:
            return True
        
        employee = db.query(EmployeeDB).filter(EmployeeDB.id == current_manager_id).first()
        if not employee:
            break
        
        visited.add(current_manager_id)
        current_manager_id = employee.manager_id
    
    return False

# Function to seed initial data
def seed_initial_data(db: Session):
    # Check if data already exists
    if db.query(EmployeeDB).count() > 0:
        return
    
    # Create the CEO (root manager)
    ceo = EmployeeDB(name="John Smith", title="CEO", manager_id=None)
    db.add(ceo)
    db.flush()  # Flush to get the ID
    
    # Create executives reporting to CEO
    cto = EmployeeDB(name="Jane Doe", title="CTO", manager_id=ceo.id)
    cfo = EmployeeDB(name="Michael Johnson", title="CFO", manager_id=ceo.id)
    coo = EmployeeDB(name="Sarah Williams", title="COO", manager_id=ceo.id)
    db.add_all([cto, cfo, coo])
    db.flush()
    
    # Create managers reporting to executives
    dev_manager = EmployeeDB(name="Robert Brown", title="Development Manager", manager_id=cto.id)
    qa_manager = EmployeeDB(name="Emily Davis", title="QA Manager", manager_id=cto.id)
    finance_manager = EmployeeDB(name="David Wilson", title="Finance Manager", manager_id=cfo.id)
    db.add_all([dev_manager, qa_manager, finance_manager])
    db.flush()
    
    # Create employees reporting to managers
    dev1 = EmployeeDB(name="Daniel Jackson", title="Senior Developer", manager_id=dev_manager.id)
    dev2 = EmployeeDB(name="Olivia Miller", title="Junior Developer", manager_id=dev_manager.id)
    qa1 = EmployeeDB(name="James Taylor", title="QA Engineer", manager_id=qa_manager.id)
    db.add_all([dev1, dev2, qa1])
    
    db.commit()

# Seed the database on startup
@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    seed_initial_data(db)
    db.close()

# Helper function to build the employee tree
def build_employee_tree(db: Session, employee_id: Optional[int] = None) -> EmployeeTree:
    if employee_id is not None:
        # Get a specific employee and their hierarchy
        employee = db.query(EmployeeDB).filter(EmployeeDB.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        return build_employee_tree_recursive(db, employee)
    else:
        # Get the root employee (the one without a manager)
        root_employee = db.query(EmployeeDB).filter(EmployeeDB.manager_id == None).first()
        if not root_employee:
            raise HTTPException(status_code=404, detail="No root manager found")
        return build_employee_tree_recursive(db, root_employee)

def build_employee_tree_recursive(db: Session, employee: EmployeeDB) -> EmployeeTree:
    tree = EmployeeTree(
        id=employee.id,
        name=employee.name,
        title=employee.title,
        manager_id=employee.manager_id,
        subordinates=[]
    )
    
    # Get direct subordinates
    subordinates = db.query(EmployeeDB).filter(EmployeeDB.manager_id == employee.id).all()
    for sub in subordinates:
        tree.subordinates.append(build_employee_tree_recursive(db, sub))
    
    return tree

# Endpoint to get all employees in tree format
@app.get("/employees/tree", response_model=EmployeeTree, summary="Get employee hierarchy as a tree")
def get_employee_tree(db: Session = Depends(get_db)):
    return build_employee_tree(db)

# Endpoint to get a specific employee's tree
@app.get("/employees/{employee_id}/tree", response_model=EmployeeTree, summary="Get specific employee's hierarchy")
def get_specific_employee_tree(employee_id: int, db: Session = Depends(get_db)):
    return build_employee_tree(db, employee_id)

# Endpoint to update employee's manager
@app.put("/employees/update-manager", summary="Update an employee's manager")
def update_employee_manager(employee_update: EmployeeUpdate, db: Session = Depends(get_db)):
    employee = db.query(EmployeeDB).filter(EmployeeDB.id == employee_update.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # If manager_id is None, we're promoting to top level
    if employee_update.manager_id is None:
        # Check if there's already a top-level manager
        existing_top = db.query(EmployeeDB).filter(EmployeeDB.manager_id == None).first()
        if existing_top and existing_top.id != employee.id:
            raise HTTPException(
                status_code=400, 
                detail="There is already a top-level manager. Demote them first."
            )
    else:
        # Check if the new manager exists
        new_manager = db.query(EmployeeDB).filter(EmployeeDB.id == employee_update.manager_id).first()
        if not new_manager:
            raise HTTPException(status_code=404, detail="Manager not found")
        
        # Check for cycles
        if has_cycle(db, employee.id, employee_update.manager_id):
            raise HTTPException(status_code=400, detail="This change would create a cycle in the hierarchy")
    
    # Update the manager_id
    employee.manager_id = employee_update.manager_id
    db.commit()
    
    return {"message": f"{employee.name}'s manager updated successfully"}

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)