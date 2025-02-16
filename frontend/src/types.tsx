export type Employee = {
  id: number;
  name: string;
  title: string;
  manager_id: number | null;
  subordinates?: Employee[] | null
}

export type OnDropFunction = (employeeId: number, managerId: number | null) => void

export type EmployeeCardProps = {
  employee: Employee;
  onDrop: OnDropFunction
}

export type ErrorData = {
  detail: string
}

export type UpdateRelationshipResponse = {
  message: string
}