import { Alert, AlertDescription } from '@/components/ui/alert'

type ErrorAlertProps = {
  message: string
}

export function ErrorAlert({ message }: ErrorAlertProps) {
  return (
    <Alert variant="destructive" className="border-destructive/25 bg-destructive/5">
      <AlertDescription className="text-destructive">{message}</AlertDescription>
    </Alert>
  )
}
