<template>
  <v-container>
    <v-row justify="center">
      presidents
    </v-row>
    <v-row justify="center">
      <!-- <v-col cols="10"> -->
        <v-tabs
          fixed-tabs
          class='ma-4'
        >
          <v-tab>
            login
          </v-tab>
          <v-tab-item class='pa-6'>
            <v-form>
              <v-text-field
                v-model="username"
                label="username"
                :rules="username_rules"
                counter
                clearable
                outlined
                shaped
              ></v-text-field>
              <v-text-field
                v-model="password"
                label="password"
                :rules="username_rules"
                counter
                clearable
                outlined
                shaped
              ></v-text-field>
              <v-row justify="center">
                <v-btn
                  color="success"
                  :disabled="!username || username.length > 5"
                  @click="send_to_game_browser"
                  height="45"
                  width="100"
                >
                  login
                </v-btn>
              </v-row>
            </v-form>
          </v-tab-item>
          <v-tab>
            register
          </v-tab>
          <v-tab-item class='pa-6'>
            <v-form>
              <v-text-field
                v-model="username"
                label="username"
                :rules="username_rules"
                counter='20'
                clearable
                outlined
                shaped
              ></v-text-field>
              <v-text-field
                v-model="password"
                label="password"
                :rules="username_rules"
                counter='40'
                clearable
                outlined
                shaped
              ></v-text-field>
              <v-text-field
                v-model="reenter_password"
                label="re enter password"
                :rules="username_rules"
                counter='40'
                clearable
                outlined
                shaped
              ></v-text-field>
              <v-row justify="center">
                <v-btn
                  color="success"
                  :disabled="!username || username.length > 5"
                  @click="send_to_game_browser"
                  height="45"
                  width="100"
                >
                  register
                </v-btn>
              </v-row>
            </v-form>
          </v-tab-item>
        </v-tabs>
      <!-- </v-col> -->
    </v-row>
    <!-- <v-row justify="center">
      
    </v-row>  -->
  </v-container>
</template>

<script>
import router from "../router";

export default {
  name: "Login",

  computed: {
    username: {
      get() {
        return this.$store.state.username;
      },

      set(username) {
        this.$store.commit("set_username", { username: username });
      }
    }
  },

  methods: {
    send_to_game_browser () {
      router.push({ name: 'game browser' });
    }
  }
};
</script>

<style scoped>
.v-btn {
  text-transform: lowercase !important;
}
.v-tab {
  text-transform: lowercase !important;
}
</style>
