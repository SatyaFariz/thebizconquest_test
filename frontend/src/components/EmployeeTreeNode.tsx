import { TreeNode } from 'react-organizational-chart'
import EmployeeCard from './EmployeeCard'
import { EmployeeCardProps } from '../types'

const EmployeeTreeNode = ({
  employee,
  onDrop
}: EmployeeCardProps) => {
  return (
    <TreeNode label={<EmployeeCard employee={employee} onDrop={onDrop} />}>
      {employee.subordinates?.map((subordinate) => (
        <EmployeeTreeNode 
          key={subordinate.id} 
          employee={subordinate} 
          onDrop={onDrop} 
        />
      ))}
    </TreeNode>
  )
}

export default EmployeeTreeNode