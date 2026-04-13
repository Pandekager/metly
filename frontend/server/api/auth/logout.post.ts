export default defineEventHandler(async (event) => {
  deleteCookie(event, 'jwt')

  return {
    success: true,
    message: 'Logged out successfully'
  }
})
