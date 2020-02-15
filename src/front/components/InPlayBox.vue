<template>
  <v-container>
    <v-row justify="center">
      <v-chip
        :active="hand_just_played"
      >
        {{ hand_just_played_count }} other players just played this hand !!
      </v-chip>
    </v-row>
    <v-row justify="center">
      <Card
        v-for="card in hand_in_play"
        :key="card"
        :card="card"
      ></Card>
      
    </v-row>
    <v-row>
      <span v-if="this.hand_in_play.length == 0">waiting for hand to be played...</span>
      <span v-else>{{ hand_in_play_desc }}</span>
    </v-row>
  </v-container>
</template>

<script>
import Card from "./Card.vue";

export default {
  name: "InPlayBox",

  components: {
    Card
  },

  props: {
    namespace: String
  },

  computed: {
    hand_in_play () {
      return this.$store.state[this.namespace].hand_in_play;
    },

    hand_in_play_desc () {
      return this.$store.state[this.namespace].hand_in_play_desc;
    },

    hand_just_played () {
      return this.$store.state[this.namespace].hand_just_played;
    },

    hand_just_played_count () {
      return this.$store.state[this.namespace].hand_just_played_count;
    }
  }
};
</script>

<style scoped>
span {
  margin: 0 auto;
}
</style>
