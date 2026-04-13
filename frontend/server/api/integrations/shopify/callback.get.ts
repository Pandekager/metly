export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase.replace('/api', '')
  const requestUrl = getRequestURL(event)
  const query = getQuery(event)
  const state = String(query.state || '')
  const expectedState = getCookie(event, 'shopify_oauth_state') || ''
  const signupFlow = getCookie(event, 'shopify_signup_flow') === '1'
  const homeUrl = new URL('/home', requestUrl.origin)

  if (!state || state !== expectedState) {
    deleteCookie(event, 'shopify_oauth_state', { path: '/' })
    deleteCookie(event, 'shopify_signup_flow', { path: '/' })
    if (signupFlow) {
      deleteCookie(event, 'jwt', { path: '/' })
    }
    homeUrl.searchParams.set('shopify', 'error')
    homeUrl.searchParams.set('reason', 'state')
    return sendRedirect(event, homeUrl.toString(), 302)
  }

  const backendUrl = new URL('integrations/shopify/callback', apiBase)
  Object.entries(query).forEach(([key, value]) => {
    if (typeof value === 'string') {
      backendUrl.searchParams.set(key, value)
    }
  })

  try {
    const response = await $fetch<{ success: boolean; shop: string }>(backendUrl.toString(), {
      method: 'GET'
    })

    const status = await $fetch<{ connected: boolean; shop?: string; has_access_token?: boolean }>('/api/integrations/shopify/status', {
      method: 'GET',
      headers: {
        cookie: getHeader(event, 'cookie') || ''
      }
    })

    deleteCookie(event, 'shopify_oauth_state', { path: '/' })
    deleteCookie(event, 'shopify_signup_flow', { path: '/' })
    if (signupFlow) {
      homeUrl.searchParams.set('created', '1')
      homeUrl.searchParams.set('processing', '1')
      if (status.shop || response.shop) {
        homeUrl.searchParams.set('shop', status.shop || response.shop)
      }
      return sendRedirect(event, homeUrl.toString(), 302)
    }
    homeUrl.searchParams.set('shopify', response.success && status.connected ? 'connected' : 'error')
    if (status.shop || response.shop) {
      homeUrl.searchParams.set('shop', status.shop || response.shop)
    }
    if (!status.connected) {
      homeUrl.searchParams.set('reason', status.has_access_token === false ? 'missing-token' : 'db-validation')
    }
    return sendRedirect(event, homeUrl.toString(), 302)
  } catch (error: any) {
    deleteCookie(event, 'shopify_oauth_state', { path: '/' })
    deleteCookie(event, 'shopify_signup_flow', { path: '/' })
    if (signupFlow) {
      deleteCookie(event, 'jwt', { path: '/' })
    }
    homeUrl.searchParams.set('shopify', 'error')
    homeUrl.searchParams.set('reason', error?.data?.detail || 'callback')
    return sendRedirect(event, homeUrl.toString(), 302)
  }
})
