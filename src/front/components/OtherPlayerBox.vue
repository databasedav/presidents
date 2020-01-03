<template>
  <v-container>
    <v-row justify="center" >
      <v-col cols="6">
        <PlayerStrip
          :namespace="this.namespace"
          :spot="this.center_spot"
        ></PlayerStrip>
      </v-col>
    </v-row>

    <v-row justify="center" >
      <v-col cols="6">
        <PlayerStrip
          :namespace="this.namespace"
          :spot="this.left_spot"
        ></PlayerStrip>
      </v-col>
      <v-col cols="6">
        <PlayerStrip
          :namespace="this.namespace"
          :spot="this.right_spot"
        ></PlayerStrip>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import PlayerStrip from "./PlayerStrip.vue";

export default {
  components: {
    PlayerStrip
  },
  props: {
    namespace: String
  },
  computed: {
    spot () {
      return this.$store.state[this.namespace].spot;
    },

    left_spot () {
      return (this.spot + 1) % 4;
    },

    center_spot () {
      return (this.spot + 2) % 4;
    },

    right_spot () {
      return (this.spot + 3) % 4;
    }
  }
};
</script>
