export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase.replace('/api', '')

  const cookie = getCookie(event, 'jwt')
  const token = cookie || getHeader(event, 'authorization')?.replace(/^Bearer\s+/i, '') || ''

  const userId = getQuery(event).user_id as string | undefined

  const url = new URL('forecast_business_advice', apiBase)
  if (userId) url.searchParams.set('user_id', userId)

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
        message: error?.message || 'Failed to fetch forecasts'
      })
    }
  }
})
