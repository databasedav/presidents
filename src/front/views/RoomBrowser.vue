<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title class="logo">
        presidents
      </v-toolbar-title>
      <v-divider class="mx-2" inset vertical></v-divider>
      <v-spacer></v-spacer>
      <v-btn color="success" @click="this.refresh">
        refresh
      </v-btn>
      <v-dialog v-model="dialog" max-width="500px">
        <v-btn slot="activator" color="primary" dark class="mb-2">
          create room
        </v-btn>
        <v-card>
          <v-card-title>
            <span class="headline">
              new room
            </span>
          </v-card-title>
          <v-card-text>
            <v-container grid-list-md>
              <v-layout wrap>
                <v-flex xs12 sm6 md4>
                  <v-text-field
                    v-model="name"
                    label="name"
                  ></v-text-field>
                </v-flex>
              </v-layout>
            </v-container>
          </v-card-text>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="blue darken-1" flat @click="close">
              cancel
            </v-btn>
            <v-btn
              color="blue darken-1"
              flat
              @click="add_room"
              :loading='loading'
            >
              create
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-toolbar>
    <v-data-table
      :headers="headers"
      :items="rooms"
      class="elevation-1"
    >
      <template slot="items" slot-scope="props">
        <td>
          {{ props.item.room }}
        </td>
        <td class="text-xs-center">
          {{ props.item.num_players }}
        </td>
        <td class="justify-center layout px-0">
          <v-btn
            color="success"
            :disabled="props.item.num_players >= 4"
            @click='join_room(props.item.rid)'
          >
            join room
          </v-btn>
        </td>
      </template>
      <template slot="no-data">
        <v-alert
          :value="true"
          color="error"
          icon="warning"
        >
          sorr no one playin rn create a new room :))
        </v-alert>
      </template>
    </v-data-table>
  </div>
</template>

<script>
import VueSocketio from 'vue-socket.io-extended'
import io from 'socket.io-client'
import { mapState } from 'vuex'
import { room_browser_plugin } from '../store/plugins'
import { create_room_browser_socket_plugin } from '../store/plugins'


export default {
  data() {
    return {
      dialog: false,
      headers: [
        {
          text: "room",
          align: "center",
          sortable: false,
          value: "room"
        },
        {
          text: "# players",
          align: "center",
          value: "num_players"
        },
        {
          text: "",
          align: "right",
          sortable: false
        }
      ],
      name: "",
      loading: false
    };
  },

  beforeCreate() {
    this.$store.dispatch('plugin_room_browser')
  },

  created() {
    this.refresh()
  },

  watch: {

    rooms () {
      // this will fire when the server force refreshes when a room is successfully added
      this.loading = false
      this.close()
    }
  },

  computed: {
    ...mapState([
      'server'
    ]),

    // room browser namespace
    rbnsp () {
      return 'room_browser-' + this.server
    },

    socket () {
      return this.$store.state[this.rbnsp].socket
    },

    rooms () {
      return this.$store.state[this.rbnsp].rooms
    }
  },

  methods: {

    refresh () {
      this.socket.emit("refresh")
    },

    close () {
      this.name = ''
      this.dialog = false;
    },

    add_room () {
      this.loading = true
      this.socket.emit('add_room', {name: this.name})
    },

    join_room (rid) {
      this.socket.emit('join_room', {rid: rid, name: this.nickname})
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
