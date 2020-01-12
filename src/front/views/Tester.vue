<template>
  <v-row>
    <v-col cols="6" v-for="i in 4">
      <Game
        :game_id="game_id"
        :testing="true"
        :testing_sid_index="i"
      ></Game>
    </v-col>
  </v-row>
</template>

<script>
import Game from "../components/Game.vue";
import axios from 'axios'

export default {
  name: "Tester",
  components: {
    Game
  },

  data () {
    return {
      game_id: null
    }
  },

  created () {
    axios.post('http://0.0.0.0:8001/create_game', {
      name: 'test',
      turn_time: .2,
      reserve_time: 0,
      trading_time: 1,
      giving_time: 1
    }).then(response => {
      this.game_id = response.data.game_id
    })
  }

};
</script>

<style></style>
