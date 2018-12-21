<template>
  <div id='app'>
    <v-app>
      <Player :namespace='"a"'></Player>
      <Player :namespace='"b"'></Player>
      <Player :namespace='"c"'></Player>
      <Player :namespace='"d"'></Player>
      <!-- <v-btn to='/serverbrowser'>Server Browser</v-btn>
      <v-btn to='/stats'>Statistics</v-btn>
      <v-btn to='/tester'>Tester</v-btn>
      <router-view/> -->
      <!-- <v-container grid-list-md text-xs-center >
        <v-layout row wrap>
          <v-flex xs12>
            <ButtonBox/>
          </v-flex>
          <v-flex xs12>
            
          </v-flex>
          <v-flex xs12>
            <Player :namespace='"b"'></Player>
          </v-flex>
          <v-flex xs12>
            <Player :namespace='"c"'></Player>
          </v-flex>
          <v-flex xs12>
            <Player :namespace='"d"'></Player>
          </v-flex>
          <v-flex xs12>
            <StoredHandBox/>
          </v-flex>
        </v-layout>
      </v-container> -->
      <!-- <iframe> <ButtonBox/> </iframe>
      <iframe> <ButtonBox/> </iframe>
      <iframe> <ButtonBox/> </iframe>
      <iframe> <ButtonBox/> </iframe> -->
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
import Receiver from './components/Receiver'
import Player from './components/Player'
// import AlertSnackbar from './components/AlertSnackbar'

export default {
  name: 'app',
  components: {
    Card,
    CardBox,
    ButtonBox,
    Hand,
    StoredHandBox,
    CurrentHandBox,
    Receiver,
    Player
    // AlertSnackbar
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
