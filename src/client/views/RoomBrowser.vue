<template>
  <div>
    <v-toolbar flat color="white">
      <v-toolbar-title class="logo">presidents</v-toolbar-title>
      <v-divider class="mx-2" inset vertical></v-divider>
      <v-spacer></v-spacer>
      <v-btn color="success" @click="this.refresh">refresh</v-btn>
      <v-dialog v-model="dialog" max-width="500px">
        <v-btn slot="activator" color="primary" dark class="mb-2">create room</v-btn>
        <v-card>
          <v-card-title>
            <span class="headline">new room</span>
          </v-card-title>
          <v-card-text>
            <v-container grid-list-md>
              <v-layout wrap>
                <v-flex xs12 sm6 md4>
                  <v-text-field
                    v-model="new_room"
                    label="room"
                    :rules="[this.rule]"
                  ></v-text-field>
                </v-flex>
              </v-layout>
            </v-container>
          </v-card-text>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="blue darken-1" flat @click="close">cancel</v-btn>
            <v-btn
              color="blue darken-1"
              flat
              @click="save"
              :loading='loading'
              :disabled="!this.room_dne || loading"
            >create & join</v-btn>
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
        <td>{{ props.item.room }}</td>
        <td class="text-xs-center">{{ props.item.num_players }}</td>
        <td class="justify-center layout px-0">
          <v-btn
            color="success"
            :disabled="props.item.num_players === 4"
            to='/presidents'
          >join room</v-btn>
        </td>
      </template>
      <template slot="no-data">
        <v-alert
          :value="true"
          color="error"
          icon="warning"
        >sorr no one playin rn create a new room :))</v-alert>
      </template>
    </v-data-table>
  </div>
</template>

<script>
import { mapState } from "vuex";

import { create_room_browser_socket_plugin } from "../store/plugins";

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
      new_room: "",
      loading: false
    };
  },

  beforeCreate() {
    this.$store.commit("attach_socket");
  },

  created() {
    const plugin = create_room_browser_socket_plugin(this.socket);
    plugin(this.$store);
    this.refresh()
  },

  watch: {
    new_room () {
      if (!this.room_dne) {
        this.$store.commit('set_room_dne', {room_dne: true})
      }
    },

    rooms () {
      // this will fire when the server force refreshes when a room is successfully added
      this.loading = false
      this.close()
    },

    room_dne (val) {
      if (!val) {  // when room already exists
        this.loading = false
      }
    }
  },

  computed: {
    ...mapState({
      socket: 'socket',
      rooms: 'rooms',
      room_dne: 'room_dne'
    }),

    rule () {
      return this.room_dne || "this room already exists"
    }
  },

  methods: {
    refresh () {
      this.socket.emit("refresh");
    },

    close () {
      this.new_room = ''
      this.dialog = false;
    },

    save () {
      this.loading = true
      this.socket.emit('create_room', {room: this.new_room});
    }
  }
};
</script>

<style scoped>
.logo {
  color: black;
  font-family: "Pacifico", cursive;
  font-size: 25pt;
}

.v-btn {
  text-transform: lowercase !important;
}
</style>
