<template>
  <div>
    <v-layout>
      <v-flex>
        <OtherPlayer
         :namespace='this.namespace'
         :spot='this.left_spot'
        >
        </OtherPlayer>
      </v-flex>
      <v-flex>
        <OtherPlayer
         :namespace='this.namespace'
         :spot='this.center_spot'
        >
        </OtherPlayer>
      </v-flex>
      <v-flex>
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
</style>
