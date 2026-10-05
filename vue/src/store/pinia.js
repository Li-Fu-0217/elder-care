import { createPinia } from 'pinia'
import { piniaPersistPlugin } from '@/plugins/piniaPersist'

const pinia = createPinia()
pinia.use(piniaPersistPlugin)

export default pinia
