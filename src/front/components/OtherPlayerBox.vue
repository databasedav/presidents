<template>
  <v-container grid-list-xl pa-0>
    <v-layout justify-center>
      <v-flex id='center' xs6>
        <PlayerStrip
         :namespace='this.namespace'
         :spot='this.center_spot'
        >
        </PlayerStrip>
      </v-flex>
    </v-layout>
    <v-layout justify-space-between>
      <v-flex id='left' xs6>
        <PlayerStrip
         :namespace='this.namespace'
         :spot='this.left_spot'
        >
        </PlayerStrip>
      </v-flex>
      <v-flex id='right' xs6>
        <PlayerStrip
         :namespace='this.namespace'
         :spot='this.right_spot'
        >
        </PlayerStrip>
      </v-flex>
    </v-layout>
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
    spot() {
      return this.$store.state[this.namespace].spot;
    },

    left_spot() {
      return (this.spot + 1) % 4
    },

    center_spot() {
      return (this.spot + 2) % 4
    },

    right_spot() {
      return (this.spot + 3) % 4
    }
  }
};
</script>
