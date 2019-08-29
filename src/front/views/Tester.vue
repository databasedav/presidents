<template>
  <v-layout row wrap>
    <v-flex xs6>
      <Game
        :server='"/server=dev"'
        :testing='true'
      ></Game>
    </v-flex>
    <v-flex xs6>
      <Game
        :server='"/server=dev"'
        :testing='true'
      ></Game>
    </v-flex>
    <v-flex xs6>
      <Game
        :server='"/server=dev"'
        :testing='true'
      ></Game>
    </v-flex>
    <v-flex xs6>
      <Game
        :server='"/server=dev"'
        :testing='true'
      ></Game>
    </v-flex>
  </v-layout>
</template>

<script>
import Game from '../components/Game.vue'

export default {
    name: 'Tester',
    components: {
        Game
    }
}
</script>

<style>

</style>
