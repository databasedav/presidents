import Vue from 'vue'
import VueSocketio from 'vue-socket.io-extended'
import App from './App.vue'
import store from './store'

Vue.config.productionTip = false
// Vue.use(VueSocketio, `//${window.location.host}`, store)

new Vue({
  store,
  render: h => h(App)
}).$mount('#app')
