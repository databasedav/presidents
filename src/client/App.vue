<template>
  <div id="app">
    <StoredHandBox/>
    <ButtonBox/>
    <CardBox/>
  </div>
</template>

<script>
import HelloWorld from './components/HelloWorld.vue'
import Card from './components/Card'
import CardBox from './components/CardBox'
import ButtonBox from './components/ButtonBox'
import Hand from './components/Hand'
import StoredHandBox from './components/StoredHandBox'

export default {
  name: 'app',
  components: {
    Card,
    CardBox,
    ButtonBox,
    Hand,
    StoredHandBox
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
  margin-top: 60px;
}
</style>
