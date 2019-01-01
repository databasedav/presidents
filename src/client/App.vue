<template>
  <div id="app">
    <v-app>
      <Tester/>
      <!-- <router-view/> -->
    </v-app>
  </div>
</template>

<script>
import Home from './views/Home.vue'
import Tester from './views/Tester.vue'

export default {
  name: "app",
  components: {
    Home,
    Tester
  }
};
</script>

<style>
#app {
  font-family: "Avenir", Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 20px;
}
</style>
