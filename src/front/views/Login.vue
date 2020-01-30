<template>
  <v-container>
    <v-row justify="center">
      presidents
    </v-row>
    <v-snackbar
      v-model="snackbar"
      :top="true"
      :timeout="1500"
    >
      {{ this.alert }}
    </v-snackbar>
    <v-row justify="center">
        <v-tabs
          fixed-tabs
          class='ma-4'
        >
          <v-tab>
            login
          </v-tab>
          <v-tab-item class='pa-6'>
            <v-form ref="login_form">
              <v-text-field
                v-model="this.username"
                label="username"
                :rules="[required]"
                counter
                clearable
                outlined
                shaped
                @change="this.login_disabled = !this.$refs.login_form.validate()"
              ></v-text-field>
              <v-text-field
                v-model="this.password"
                label="password"
                :rules="[required]"
                :append-icon="this.show_login_password ? 'mdi-eye' : 'mdi-eye-off'"
                :type="this.show_login_password ? 'text' : 'password'"
                counter
                clearable
                outlined
                shaped
                @click:append="this.show_login_password = !this.show_login_password"
                @change="this.login_disabled = !this.$refs.login_form.validate()"
              ></v-text-field>
              <v-row justify="center">
                <v-btn
                  color="success"
                  :disabled="this.login_disabled"
                  @click="this.login"
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
            <v-form ref="register_form">
              <v-text-field
                v-model="this.username"
                label="username"
                :rules="this.username_rules"
                clearable
                outlined
                shaped
                counter='20'
                @change="this.register_disabled = !this.$refs.register_form.validate()"
              ></v-text-field>
              <v-text-field
                v-model="this.password"
                label="password"
                :rules="this.password_rules"
                icon
                :append-icon="this.show_register_password ? 'mdi-eye' : 'mdi-eye-off'"
                :type="this.show_register_password ? 'text' : 'password'"
                clearable
                outlined
                shaped
                counter='40'
                @click:append="this.show_register_password = !this.show_register_password"
                @change="this.register_disabled = !this.$refs.register_form.validate()"
              ></v-text-field>
              <v-text-field
                v-model="this.reenter_password"
                label="re enter password"
                :rules="this.reenter_password_rules"
                :append-icon="this.show_register_reenter_password ? 'mdi-eye' : 'mdi-eye-off'"
                :type="this.show_register_reenter_password ? 'text' : 'password'"
                counter
                clearable
                outlined
                shaped
                @click:append="this.show_register_reenter_password = !this.show_register_reenter_password"
                @change="this.register_disabled = !this.$refs.register_form.validate()"
              ></v-text-field>
              <v-row justify="center">
                <v-btn
                  color="success"
                  :disabled="this.register_disabled"
                  @click="this.register"
                  height="45"
                  width="100"
                >
                  register
                </v-btn>
              </v-row>
            </v-form>
          </v-tab-item>
        </v-tabs>
    </v-row>
  </v-container>
</template>

<script>
import router from "../router";
import axios from "axios"

// TODO: fix hide password eye

export default {
  name: "Login",

  data () {
    const required = x => !!x || 'required'
    return {
      username: '',
      password: '',
      reenter_password: '',
      show_login_password: false,
      show_register_password: false,
      show_register_reenter_password: false,
      required,
      username_rules: [
        required,
        // length requirement
        x => 1 <= x.length <= 20 || 'must be between 1 and 20 characters',
        // letters, numbers, and underscores only
        x => /^[a-zA-Z0-9_]+$/.test(x)  || 'letters, numbers, and underscores only',
        // not all numbers
        x => !/^[0-9]+$/.test(x) || "can't be all numbers",
        // not all underscores
        x => !/^_+$/.test(x) || "can't be all underscores"
      ],
      password_rules: [
        required,
        // length requirement
        x => 8 <= x.length <= 40 || 'must be between 8 and 40 characters',
      ],
      login_disabled: false,
      register_disabled: false,
      snackbar: false,
      alert: ''
    }
  },

  computed: {
    // this one is computed because it involved data
    // TODO: this isn't working
    reenter_password_rules () {
      return [
        this.required,
        // x => undefined === this.password || 'passwords must match'
      ]
    }
  },

  methods: {
    login () {
      axios.post('/token', {
        username: payload.username,
        password: payload.password
      }).then(response => {
        router.push({ name: 'game browser' })
      }).catch(error => {
        console.log(error)
      })
    },

    register () {
      self = this
      axios.post('/register', {
        username: self.username,
        password: self.password,
        reenter_password: self.reenter_password
      }).then(response => {
        self.alert = response.data.alert
      }).catch(error => {
        self.alert = error.response.data
        console.log(error.response)
      })
    }
  },
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
