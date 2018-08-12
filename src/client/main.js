import Vue from 'vue'
import VueSocketio from 'vue-socket.io-extended'
import io from 'socket.io-client'
import App from './App.vue'
import store from './store'
import router from './router'
import Vuetify from 'vuetify'
import SnackbarStackPlugin from 'snackbarstack'

import 'vuetify/dist/vuetify.min.css'

Vue.config.productionTip = false

Vue.use(Vuetify);
Vue.use(VueSocketio, io(`//${window.location.host}`), { store })
Vue.use(SnackbarStackPlugin, { duration: 3000 })

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
