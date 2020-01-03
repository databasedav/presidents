<template>
  <v-snackbar v-model="snackbar" top="true">
    {{ alert }}
    <v-btn color="pink" flat @click="snackbar = false">
      Close
    </v-btn>
  </v-snackbar>
</template>

<script>
import { mapGetters } from "vuex";

export default {
  name: "AlertSnackbar",

  props: {
    namespace: String
  },

  computed: {
    snackbar() {
      return this.$store.state[this.namespace].snackbar;
    },
    alert() {
      return this.$store.state[this.namespace].alert;
    }
  }
};
</script>
