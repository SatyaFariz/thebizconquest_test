import React, { useRef } from 'react'
import { useDrag, useDrop } from 'react-dnd'
import { Employee, EmployeeCardProps } from '../types'

const EmployeeCard: React.FC<EmployeeCardProps> = ({ employee, onDrop }) => {
  const ref = useRef<HTMLDivElement>(null);

  const [{ isDragging }, drag] = useDrag(() => ({
    type: 'EMPLOYEE',
    item: employee,
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging(),
    }),
  }));

  const [, drop] = useDrop(() => ({
    accept: 'EMPLOYEE',
    drop: (draggedItem: Employee) => {
      if (draggedItem.id !== employee.id && draggedItem.manager_id !== employee.id) {
        onDrop(draggedItem.id, employee.id);
      }
    },
  }));

  drag(drop(ref));

  return (
    <div
      ref={ref}
      className={`p-4 !bg-gray-100 border border-gray-200 rounded bg-white cursor-move transition-opacity ${
        isDragging ? "opacity-50" : "opacity-100"
      }`}
    >
      <h3 className="text-lg font-bold">{employee.name}</h3>
      <p className="text-sm text-gray-600">{employee.title}</p>
      <p className="text-xs text-gray-400">ID: {employee.id}</p>
      {employee.manager_id && (
        <p className="text-xs text-gray-400">Manager ID: {employee.manager_id}</p>
      )}
    </div>
  );
};

export default EmployeeCard;
