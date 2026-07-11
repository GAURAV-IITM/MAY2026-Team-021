function getErrorDetails(error) {
  if (error instanceof Error) return error
  return new Error(String(error || 'Unknown application error'))
}

export function installGlobalErrorHandling(app, router) {
  let isRedirecting = false

  async function handleError(error, context) {
    const normalizedError = getErrorDetails(error)
    console.error(`[${context}]`, normalizedError)

    if (router.currentRoute.value.name === 'serverError' || isRedirecting) return

    isRedirecting = true
    const failedRoute = router.currentRoute.value.fullPath

    try {
      await router.replace({
        name: 'serverError',
        query: failedRoute ? { from: failedRoute } : undefined,
      })
    } catch (navigationError) {
      console.error('[Error page navigation]', navigationError)
    } finally {
      isRedirecting = false
    }
  }

  app.config.errorHandler = (error, _instance, info) => {
    void handleError(error, `Vue error: ${info}`)
  }

  router.onError((error) => {
    void handleError(error, 'Router error')
  })

  window.addEventListener('error', (event) => {
    void handleError(event.error || event.message, 'Window error')
  })

  window.addEventListener('unhandledrejection', (event) => {
    void handleError(event.reason, 'Unhandled promise rejection')
  })
}
