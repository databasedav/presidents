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
          create server
        </v-btn>
        <v-card>
          <v-card-title>
            <span class="headline">
              new server
            </span>
          </v-card-title>
          <v-card-text>
            <v-container grid-list-md>
              <v-layout wrap>
                <v-flex xs12 sm6 md4>
                  <v-text-field v-model="name" label="name"></v-text-field>
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
              @click="add_server"
              :loading="loading"
            >
              create
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-toolbar>
    <v-data-table :headers="headers" :items="servers" class="elevation-1">
      <template slot="items" slot-scope="props">
        <td>
          {{ props.item.name }}
        </td>
        <td class="text-xs-center">
          {{ props.item.num_players }}
        </td>
        <td class="justify-center layout px-0">
          <v-btn
            color="success"
            :disabled="props.item.num_players >= 4"
            @click="join_server(props.item.rid)"
          >
            join server
          </v-btn>
        </td>
      </template>
      <template slot="no-data">
        <v-alert :value="true" color="error" icon="warning">
          sorr no one playin rn create a new server :))
        </v-alert>
      </template>
    </v-data-table>
  </div>
</template>

<script>
import io from "socket.io-client";
import { mapState } from "vuex";
import { server_browser_plugin } from "../store/plugins";
import { create_server_browser_socket_plugin } from "../store/plugins";

export default {
  data () {
    return {
      dialog: false,
      headers: [
        {
          text: "server",
          align: "center",
          sortable: false,
          value: "server"
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

  created() {
    // this.$store.dispatch("plugin_server_browser", {
    //   rbnsp: this.rbnsp
    // });
  },

  beforeMount() {
    this.refresh();
  },

  watch: {
    servers() {
      // this will fire when the server force refreshes when a server is successfully added
      if (this.loading) {
        this.close();
      }
    }
  },

  computed: {
    ...mapState(["username", "games"])
  },

  methods: {
    refresh () {
      this.$store.dispatch(`${this.rbnsp}/emit_refresh`);
    },

    close () {
      this.loading = false;
      this.name = "";
      this.dialog = false;
    },

    create_game () {
      this.loading = true;
      this.$store.dispatch('create_game', {
        name: this.name
      });
    },

    join_server (game_id) {
      this.$store.dispatch('join_game', {
        game_id: game_id,
        username: this.username,
      });
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
