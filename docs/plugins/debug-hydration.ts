export default defineNuxtPlugin(() => {
  const route = useRoute()

  if (import.meta.server) {
    console.log(`[SSR] Rendering route: ${route.fullPath} at ${new Date().toISOString()}`)
  }

  if (import.meta.client) {
    onBeforeMount(() => {
      console.log(`[CSR] Mounting route: ${route.fullPath} at ${new Date().toISOString()}`)
    })
  }

  onServerPrefetch(() => {
    if (import.meta.server) {
      console.log(`[SSR] onServerPrefetch called at route: ${route.fullPath}`)
    }
  })
})
