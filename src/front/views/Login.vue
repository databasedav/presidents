<template>
  <div>
    <v-text-field
      label="username"
      v-model="username"
      clearable
      counter
      maxlength="10"
      color="grey"
    ></v-text-field>
    <v-btn
      color="success"
      :disabled="!username"
      @click="send_to_server_browser"
    >
      browse games
    </v-btn>
  </div>
</template>

<script>
import router from "../router";

export default {
  name: "Login",

  data() {
    return {
      
    };
  },

  computed: {
    nickname: {
      get() {
        return this.$store.state.username;
      },

      set(nickname) {
        this.$store.commit("set_username", { username: username });
      }
    }
  },

  methods: {
    send_to_server_browser() {
      router.push({
        name: "server browser",
        params: {
          rbnsp: `/server_browser_${this.server}`
        }
      });
    }
  }
};
</script>

<style scoped>
.v-btn {
  text-transform: lowercase !important;
}
</style>
