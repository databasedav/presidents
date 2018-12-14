<template>
  <div id="app">
<<<<<<< HEAD
    <v-app>
      <StoredHandBox/>
      <ButtonBox/>
      <CardBox/>
    </v-app>
=======
    <!-- <AlertSnackBar/> -->
    <StoredHandBox/>
    <ButtonBox/>
    <CurrentHandBox/>
    <CardBox/>
>>>>>>> 862b65305567d81fa5982ca1bcdd8b9d67c091c0
  </div>
</template>

<script>
import HelloWorld from './components/HelloWorld.vue'
import Card from './components/Card'
import CardBox from './components/CardBox'
import ButtonBox from './components/ButtonBox'
import Hand from './components/Hand'
import StoredHandBox from './components/StoredHandBox'
import CurrentHandBox from './components/CurrentHandBox'
// import AlertSnackBar from './components/AlertSnackBar'

export default {
  name: 'app',
  components: {
    Card,
    CardBox,
    ButtonBox,
    Hand,
    StoredHandBox,
    CurrentHandBox,
    // AlertSnackBar
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 20px;
}
</style>
