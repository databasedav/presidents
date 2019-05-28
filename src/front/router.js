import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import serverBrowser from './views/ServerBrowser.vue'
import Presidents from './views/Presidents.vue'
import Tester from './views/Tester.vue'

Vue.use(Router)

export default new Router({
  mode: 'history',
  // base: 'process.env.BASE_URL',
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/server_browser',
      name: 'server browser',
      component: serverBrowser,
      props: true
    },
    // {
    //   path: '/statistics',
    //   name: 'statistics',
    //   component: Statistics
    // },
    {
      path:'/presidents',
      name: 'presidents',
      component: Presidents,
      props: true
    },
    {
      path: '/tester',
      name: 'tester',
      component: Tester
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (about.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import(/* webpackChunkName: "about" */ './views/About.vue')
    }
  ]
})
