export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase.replace('/api', '')

  const cookie = getCookie(event, 'jwt')
  const token = cookie || getHeader(event, 'authorization')?.replace(/^Bearer\s+/i, '') || ''

  const url = new URL('customer_analytics', apiBase)

  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  try {
    const res = await $fetch(url.toString(), {
      headers,
      method: 'GET'
    })
    return res
  } catch (error: any) {
    if (error?.statusCode === 401 || error?.status === 401) {
      throw createError({
        statusCode: 401,
        message: 'Unauthorized - Invalid or missing token'
      })
    } else if (error?.statusCode === 403 || error?.status === 403) {
      throw createError({
        statusCode: 403,
        message: 'Forbidden - Access denied'
      })
    } else {
      throw createError({
        statusCode: error?.statusCode || 500,
        message: error?.message || 'Failed to fetch customer analytics'
      })
    }
  }
})