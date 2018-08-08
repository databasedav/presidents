import Vue from 'vue'
import VueSocketio from 'vue-socket.io-extended'
import io from 'socket.io-client'
import App from './App.vue'
import store from './store'
import router from './router'

Vue.config.productionTip = false
Vue.use(VueSocketio, io(`//${window.location.host}`), { store })

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
