<template>
  <v-container>
    <v-snackbar
      v-model="snackbar"
      :top="true"
      :timeout="1500"
    >
      {{ alert }}
      <v-btn
        color="pink"
        text
        @click="snackbar = false"
      >
        close
      </v-btn>
    </v-snackbar>
    <v-data-table
      :headers="headers"
      :items="games"
      class="elevation-1"
      :mobile-breakpoint="0"
    >
      <template v-slot:top>
        <v-toolbar flat color="black">
          <v-toolbar-title>presidents</v-toolbar-title>
          <v-divider
            class="mx-4"
            inset
            vertical
          ></v-divider>
          <v-spacer></v-spacer>
          <v-btn
            color="success"
            :loading="refresh_loading"
            @click="refresh"
          >
            refresh
          </v-btn>
          <v-dialog v-model="dialog" max-width="500px">
            <template v-slot:activator="{ on }">
              <v-btn color="primary" dark class="mb-2" v-on="on">create game</v-btn>
            </template>
            <v-card>
              <v-card-title>
                <span class="headline">new game</span>
              </v-card-title>

              <v-card-text>
                <v-container>
                  <v-row justify="center">
                    <v-col cols="10">
                      <v-text-field
                        v-model="name"
                        label="game name"
                        clearable
                        counter="20"
                      ></v-text-field>
                    </v-col>
                  </v-row>
                  <v-row justify="center">
                    <v-col cols="10">
                      <v-text-field disabled label="password (coming soon)"></v-text-field>
                    </v-col>
                  </v-row>
                </v-container>
              </v-card-text>

              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                  color="blue darken-1"
                  text
                  @click="close"
                >
                  cancel
                </v-btn>
                <v-btn
                  color="blue darken-1"
                  :loading='create_game_loading'
                  @click="create_game"
                >
                  create game
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </v-toolbar>
      </template>
      <template v-slot:item.fresh="{ item }">
        {{ item.fresh ? 'yes' : 'no' }}
      </template>
      <template v-slot:item.join_button="{ item }">
        <v-btn
          color="success"
          :disabled="item.num_players == 4"
          :loading='join_game_loading'
          @click="join_game(item.game_id)"
        >
          join game
        </v-btn>
      </template>
      <template v-slot:no-data>
        <v-alert :value="true" type="error">
          sorry no one's playin right now; create a new game
        </v-alert>
      </template>
    </v-data-table> 
  </v-container>
</template>

<script>
import { mapState } from "vuex";
import axios from 'axios'
import io from 'socket.io-client'
import { create_game_module, EVENTS } from "../utils"

export default {
  data () {
    return {
      dialog: false,
      headers: [
        {
          text: "name",
          align: "center",
          sortable: false,
          value: "name"
        },
        {
          text: "# players",
          align: "center",
          value: "num_players"
        },
        {
          text: "fresh",
          align: "center",
          value: "fresh"
        },
        {
          text: "",
          align: "right",
          sortable: false,
          value: "join_button"
        }
      ],
      name: "",
      loading: false,
      refresh_loading: false,
      create_game_loading: false,
      join_game_loading: false
    };
  },

  created () {
    this.refresh()
  },

  computed: {
    ...mapState(["username", "games"])
  },

  methods: {
    close () {
      this.loading = false
      this.name = ""
      this.dialog = false
    },

    refresh () {
      const self = this
      axios.get('/get_games', {
        headers: {
          Authorization: `Bearer ${sessionStorage.token}`
        }
      }).then(response => {
        self.$store.state.games = response.data.games
      })
    },

    create_game () {
      const self = this
      this.create_game_loading = true
      axios.post('/create_game', {name: self.name}, {
        headers: {
          Authorization: `Bearer ${sessionStorage.token}`
        }
      }).then(response => {
        // adding a server auto joins it
        self.alert = response.data.alert
        self.snackbar = true
        self.join_game(response.data.game_id)
      }).catch(error => {
        if (error.response) {
          console.log(error.response)
          self.alert = error.response.data.detail
          self.snackbar = true
        } else {
          console.log(error.response)
        }
      }).finally(_ => {
        self.create_game_loading = false
      })
    },

    join_game (game_id) {
      const self = this
      this.join_game_loading = true
      axios.put('/join_game', {game_id: game_id}, {
        headers: {
          Authorization: `Bearer ${sessionStorage.token}`
        }
      }).then(response => {
        const socket = io('/', {  // first arg is the namespace
          path: '/socket.io',
          forceNew: true,
          reconnection: false,  // TODO: users should be prompted to reconnect on server crash
          transportOptions: {
            polling: {
              extraHeaders: {
                Authorization: `Bearer ${sessionStorage.token}`,
                game_id: game_id,
                game_key: response.data.game_key
              }
            }
          }
        })
        // if connection is succesful
        socket.once('connect', _ => {
          // game id is used as vuex namespace
          self.$store.registerModule(game_id, create_game_module())
          const commit = self.$store.commit
          commit(`${game_id}/set_socket`, {socket: socket})
          EVENTS.forEach(event => {
            socket.on(event, payload => {
              commit(`${game_id}/${event}`, payload)
            })
          })

          self.$router.push({ name: 'presidents', params: { game_id } })
        })
      }).catch(error => {
        if (error.response) {
          console.log(error.response)
          self.alert = error.response.data.detail  // failure
          self.snackbar = true
        } else {
          console.log(error.response)
        }
      }).finally(_ => {
        self.join_game_loading = false
      })
    }
  }
};
</script>

<style scoped>
.logo {
  color: white;
  font-family: "Pacifico", cursive;
  font-size: 40pt;
}

.v-btn {
  text-transform: lowercase !important;
}
</style>
