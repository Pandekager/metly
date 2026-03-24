export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase.replace('/api', '')
  const token = getCookie(event, 'jwt') || ''
  const shop = String(getQuery(event).shop || '').trim()

  if (!token) {
    throw createError({
      statusCode: 401,
      message: 'Unauthorized - Missing token'
    })
  }

  if (!shop) {
    throw createError({
      statusCode: 400,
      message: 'Shop domain is required'
    })
  }

  const requestUrl = getRequestURL(event)
  const redirectUri = `${requestUrl.origin}/api/integrations/shopify/callback`
  const backendUrl = new URL('integrations/shopify/install', apiBase)
  backendUrl.searchParams.set('shop', shop)
  backendUrl.searchParams.set('redirect_uri', redirectUri)

  try {
    const response = await $fetch<{ authorize_url: string; state: string }>(backendUrl.toString(), {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`
      }
    })

    setCookie(event, 'shopify_oauth_state', response.state, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 15,
      path: '/'
    })

    return sendRedirect(event, response.authorize_url, 302)
  } catch (error: any) {
    throw createError({
      statusCode: error?.statusCode || 500,
      message: error?.data?.detail || error?.message || 'Failed to start Shopify connection'
    })
  }
})
