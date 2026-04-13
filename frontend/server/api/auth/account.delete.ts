export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig(event)
  const apiBase = config.public.apiBase.replace('/api', '')
  const token = getCookie(event, 'jwt') || ''

  if (!token) {
    throw createError({
      statusCode: 401,
      message: 'Unauthorized - Missing token'
    })
  }

  try {
    const response = await $fetch(new URL('auth/account', apiBase).toString(), {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`
      }
    })

    deleteCookie(event, 'jwt', { path: '/' })
    return response
  } catch (error: any) {
    throw createError({
      statusCode: error?.statusCode || 500,
      message: error?.data?.detail || error?.message || 'Failed to delete account'
    })
  }
})
