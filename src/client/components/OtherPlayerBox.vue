<template>
  <div>
    <v-layout justify-space-around>
      <v-flex id='left' xs3>
        <OtherPlayer
         :namespace='this.namespace'
         :spot='this.left_spot'
        >
        </OtherPlayer>
      </v-flex>
      <v-flex id='center' xs3>
        <OtherPlayer
         :namespace='this.namespace'
         :spot='this.center_spot'
        >
        </OtherPlayer>
      </v-flex>
      <v-flex id='right' xs3>
        <OtherPlayer
         :namespace='this.namespace'
         :spot='this.right_spot'
        >
        </OtherPlayer>
      </v-flex>
    </v-layout>
  </div>
</template>

<script>
import OtherPlayer from "./OtherPlayer.vue";

export default {
  components: {
    OtherPlayer
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

<style>
/* TODO: maybe do the rotation thing */
/* #left {
  transform: rotate(-20deg);
} */
</style>
