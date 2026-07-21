import { ApiError } from '@/lib/http'

/** Map transport / API failures to short trust-friendly copy. */
export function friendlyErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.isNetworkError) {
      return 'Could not reach the assistant. Check your connection and try again.'
    }
    if (error.status === 401) {
      return 'Your session expired. Sign in again to continue.'
    }
    if (error.status === 403) {
      return 'You do not have access to that conversation.'
    }
    if (error.status === 404) {
      return 'That chat or source passage could not be found.'
    }
    if (error.message.trim() !== '') {
      return error.message
    }
    return 'Something went wrong. Please try again.'
  }

  if (error instanceof Error && error.message.trim() !== '') {
    const message = error.message
    if (/not authenticated/i.test(message)) {
      return 'Your session expired. Sign in again to continue.'
    }
    if (/network|failed to fetch/i.test(message)) {
      return 'Could not reach the assistant. Check your connection and try again.'
    }
    return message
  }

  return 'Something went wrong. Please try again.'
}
