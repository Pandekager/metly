export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase.replace('/api', '')
  const token = getCookie(event, 'jwt') || ''

  if (!token) {
    throw createError({
      statusCode: 401,
      message: 'Unauthorized - Missing token'
    })
  }

  try {
    return await $fetch(new URL('integrations/shopify/status', apiBase).toString(), {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
  } catch (error: any) {
    throw createError({
      statusCode: error?.statusCode || 500,
      message: error?.data?.detail || error?.message || 'Failed to fetch Shopify status'
    })
  }
})
