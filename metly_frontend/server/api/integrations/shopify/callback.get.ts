export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase.replace('/api', '')
  const requestUrl = getRequestURL(event)
  const query = getQuery(event)
  const state = String(query.state || '')
  const expectedState = getCookie(event, 'shopify_oauth_state') || ''
  const homeUrl = new URL('/home', requestUrl.origin)

  if (!state || state !== expectedState) {
    deleteCookie(event, 'shopify_oauth_state', { path: '/' })
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

    deleteCookie(event, 'shopify_oauth_state', { path: '/' })
    homeUrl.searchParams.set('shopify', response.success ? 'connected' : 'error')
    if (response.shop) {
      homeUrl.searchParams.set('shop', response.shop)
    }
    return sendRedirect(event, homeUrl.toString(), 302)
  } catch (error: any) {
    deleteCookie(event, 'shopify_oauth_state', { path: '/' })
    homeUrl.searchParams.set('shopify', 'error')
    homeUrl.searchParams.set('reason', error?.data?.detail || 'callback')
    return sendRedirect(event, homeUrl.toString(), 302)
  }
})
