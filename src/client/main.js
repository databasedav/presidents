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
<<<<<<< HEAD
Vue.use(SnackbarStackPlugin, {duration: 3000})
=======
Vue.use(SnackbarStackPlugin, { duration: 3000 })
>>>>>>> 862b65305567d81fa5982ca1bcdd8b9d67c091c0

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
