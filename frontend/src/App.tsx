import { Tree } from 'react-organizational-chart';
import EmployeeCard from './components/EmployeeCard';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Employee, ErrorData, UpdateRelationshipResponse } from './types';
import EmployeeTreeNode from './components/EmployeeTreeNode';
import Spinner from './components/Spinner';
import { Toaster, toast } from 'react-hot-toast';
import { useEffect } from 'react';

const queryKey = ['employee_tree']

const App = () => {
  const queryClient = useQueryClient()
  const { isPending, error, data } = useQuery({
    queryKey,
    queryFn: (): Promise<Employee> =>
      fetch('/api/employees/tree').then((res) =>
        res.json(),
      ),
  })

  const updateRelationshipMutation = useMutation({
    mutationFn: async (body: { employee_id: number, manager_id: number | null }): Promise<UpdateRelationshipResponse> => {
      const res = await fetch('/api/employees/update-manager', {
        method: 'PUT',
        body: JSON.stringify(body),
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!res.ok) {
        const errorData: ErrorData = await res.json();
        throw new Error(errorData.detail);
      }

      return res.json();
    },
  })

  const handleDrop = (employeeId: number, managerId: number | null) => {
    const toastDuration = 3000
    updateRelationshipMutation.mutate({ 
      employee_id: employeeId, 
      manager_id: managerId
    }, {
      onError: (error) => {
        console.log(error)
        toast.error(error.message, { duration: toastDuration })
      },
      onSuccess: (data) => {
        toast.success(data.message, { duration: toastDuration })
        queryClient.invalidateQueries({ queryKey })
      }
    })
  }

  useEffect(() => {
    toast.success(
      'You can drag an employee card and drop it onto another to update their reporting relationship',
      {
        duration: 10000
      }
    )
  }, [])

  if (isPending)  return (
    <div className="flex justify-center items-center h-[100vh]">
      <Spinner/>
    </div>
  )

  if (error) return 'An error has occurred: ' + error.message

  return (
    <div className="flex p-6 justify-center">
      <Tree
        lineWidth="2px"
        lineColor="red"
        lineBorderRadius="10px"
        label={
          <EmployeeCard 
            employee={data}
            onDrop={handleDrop}
          />
        }
      >
        {data.subordinates?.map((subordinate: Employee) => {
          return (
            <EmployeeTreeNode
              key={subordinate.id} 
              employee={subordinate} 
              onDrop={handleDrop} 
            />
          )
        })}
      </Tree>

      <Toaster
        position="bottom-left"
      />
    </div>
  )
};

export default App;