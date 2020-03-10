<template>
  <v-container>
    <v-row justify="center">
      <img id='logo' alt='presidents logo' src='../assets/logo.svg' width="80%">
    </v-row>
    <v-snackbar
      v-model="snackbar"
      :top="true"
      :timeout="1500"
    >
      {{ this.alert }}
      <v-btn
        color="pink"
        text
        @click="snackbar = false"
      >
        close
      </v-btn>
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
                v-model="username"
                label="username"
                :rules="[required]"
                counter
                clearable
                outlined
                shaped
                @input="_ => password && login_validate()"
              ></v-text-field>
              <v-text-field
                v-model="password"
                label="password"
                :rules="[required]"
                :append-icon="show_login_password ? 'mdi-eye' : 'mdi-eye-off'"
                :type="show_login_password ? 'text' : 'password'"
                counter
                clearable
                outlined
                shaped
                @click:append="show_login_password = !show_login_password"
                @input="_ => username && login_validate()"
              ></v-text-field>
              <v-row justify="center">
                <v-btn
                  color="success"
                  :disabled="login_disabled"
                  :loading="login_loading"
                  @click="login"
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
                v-model="username"
                label="username"
                :rules="username_rules"
                clearable
                outlined
                shaped
                counter='20'
                @input="_ => password && reenter_password && register_validate()"
              ></v-text-field>
              <v-text-field
                v-model="password"
                label="password"
                :rules="password_rules"
                icon
                :append-icon="show_register_password ? 'mdi-eye' : 'mdi-eye-off'"
                :type="show_register_password ? 'text' : 'password'"
                clearable
                outlined
                shaped
                counter='40'
                @click:append="show_register_password = !show_register_password"
                @input="_ => username && reenter_password && register_validate()"
              ></v-text-field>
              <v-text-field
                v-model="reenter_password"
                label="re enter password"
                :rules="reenter_password_rules"
                :append-icon="show_register_reenter_password ? 'mdi-eye' : 'mdi-eye-off'"
                :type="show_register_reenter_password ? 'text' : 'password'"
                counter
                clearable
                outlined
                shaped
                @click:append="show_register_reenter_password = !show_register_reenter_password"
                @input="_ => username && password && register_validate()"
              ></v-text-field>
              <v-row justify="center">
                <v-btn
                  color="success"
                  :disabled="register_disabled"
                  :loading="register_loading"
                  @click="register"
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
        // TODO: length requirements not working
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
      reenter_password_rules: [
        required,
        x => x === this.password || 'passwords must match'
      ],
      login_disabled: true,
      register_disabled: true,
      login_loading: false,
      register_loading: false,
      snackbar: false,
      alert: ''
    }
  },

  methods: {
    login_validate () {
      this.login_disabled = !this.$refs.login_form.validate()
    },

    register_validate () {
      this.register_disabled = !this.$refs.register_form.validate()
    },

    login () {
      var form_data = new FormData()
      form_data.set('username', this.username)
      form_data.set('password', this.password)
      const self = this
      this.login_loading = true
      axios.post('https://presidentsdotcom.azurewebsites.net/token', form_data).then(response => {
        sessionStorage.token = response.data.access_token
        self.$store.username = self.username
        router.push({ name: 'game browser' })
      }).catch(error => {
        if (error.response) {
          console.log(error.response)
          self.alert = error.response.data.detail  // failure
          self.snackbar = true
        } else {
          console.log(error)
        }
      }).finally(_ => {
        self.login_loading = false
      })
    },

    register () {
      // TODO: snap to 
      const self = this
      this.register_loading = true
      axios.post('https://presidentsdotcom.azurewebsites.net/register', {
        username: self.username,
        password: self.password,
        reenter_password: self.reenter_password
      }).then(response => {
        self.alert = response.data.alert  // success
        self.snackbar = true
        self.login_validate()
      }).catch(error => {
        if (error.response) {
          console.log(error.response)
          self.alert = error.response.data.detail  // failure
          self.snackbar = true
        } else {
          console.log(error)
        }
      }).finally(_ => {
        self.register_loading = false
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
