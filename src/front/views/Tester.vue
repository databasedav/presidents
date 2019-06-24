<template>
  <v-layout row wrap>
    <v-flex xs6>
      <iframe>
        <Player :rnsp='"/server_test"'></Player>
      </iframe>
    </v-flex>
    <v-flex xs6>
      <iframe>
        <Player :rnsp='"/server_test"'></Player>
      </iframe>
    </v-flex>
    <v-flex xs6>
      <iframe>
        <Player :rnsp='"/server_test"'></Player>
      </iframe>
    </v-flex>
    <v-flex xs6>
      <iframe>
        <Player :rnsp='"/server_test"'></Player>
      </iframe>
    </v-flex>
  </v-layout>
</template>

<script>
import Player from '../components/Player.vue'

export default {
    name: 'Tester',
    components: {
        Player
    }
}
</script>

<style>

</style>
