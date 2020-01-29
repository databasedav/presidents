<template>
  <v-data-table
    :headers="headers"
    :items="games"
    class="elevation-1"
    mobile-breakpoint=""
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
        <v-btn color="success" @click="refresh">
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
                    <v-text-field v-model="name" label="game name" clearable counter maxlength="20"></v-text-field>
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
              <v-btn color="blue darken-1" text @click="close">cancel</v-btn>
              <v-btn color="blue darken-1" text @click="create_game">create game</v-btn>
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
</template>

<script>
import { mapState } from "vuex";

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
      loading: false
    };
  },

  created () {
    this.refresh()
  },

  computed: {
    ...mapState(["username", "games"])
  },

  methods: {
    refresh () {
      this.$store.dispatch('refresh_games');
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

    join_game (game_id) {
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
