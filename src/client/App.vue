<template>
  <div id='app'>
    <v-app>
      <!-- <v-btn to='/serverbrowser'>Server Browser</v-btn>
      <v-btn to='/stats'>Statistics</v-btn>
      <v-btn to='/tester'>Tester</v-btn>
      <router-view/> -->
      <v-container grid-list-md text-xs-center >
        <v-layout row wrap>
          <v-flex xs12>
            <ButtonBox/>
          </v-flex>
          <v-flex xs12>
            <CardBox/>
          </v-flex>
          <v-flex xs12>
            <StoredHandBox/>
          </v-flex>
        </v-layout>
      </v-container>
    </v-app>
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
