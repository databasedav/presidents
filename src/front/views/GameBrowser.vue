<template>
  <v-data-table
    :headers="headers"
    :items="games"
    class="elevation-1"
  >
    <template v-slot:top>
      <v-toolbar flat color="white">
        <v-toolbar-title>presidents</v-toolbar-title>
        <v-divider
          class="mx-4"
          inset
          vertical
        ></v-divider>
        <v-spacer></v-spacer>
        <v-dialog v-model="dialog" max-width="500px">
          <template v-slot:activator="{ on }">
            <v-btn color="primary" dark class="mb-2" v-on="on">New Item</v-btn>
          </template>
          <v-card>
            <v-card-title>
              <span class="headline">{{ formTitle }}</span>
            </v-card-title>

            <v-card-text>
              <v-container>
                <v-row>
                  <v-col cols="12" sm="6" md="4">
                    <v-text-field v-model="editedItem.name" label="Dessert name"></v-text-field>
                  </v-col>
                  <v-col cols="12" sm="6" md="4">
                    <v-text-field v-model="editedItem.calories" label="Calories"></v-text-field>
                  </v-col>
                  <v-col cols="12" sm="6" md="4">
                    <v-text-field v-model="editedItem.fat" label="Fat (g)"></v-text-field>
                  </v-col>
                  <v-col cols="12" sm="6" md="4">
                    <v-text-field v-model="editedItem.carbs" label="Carbs (g)"></v-text-field>
                  </v-col>
                  <v-col cols="12" sm="6" md="4">
                    <v-text-field v-model="editedItem.protein" label="Protein (g)"></v-text-field>
                  </v-col>
                </v-row>
              </v-container>
            </v-card-text>

            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn color="blue darken-1" text @click="close">Cancel</v-btn>
              <v-btn color="blue darken-1" text @click="save">Save</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </v-toolbar>
    </template>
    <template v-slot:item.action="{ item }">
      <v-icon
        small
        class="mr-2"
        @click="editItem(item)"
      >
        edit
      </v-icon>
      <v-icon
        small
        @click="deleteItem(item)"
      >
        delete
      </v-icon>
    </template>
    <template v-slot:no-data>
      <v-btn color="primary" @click="initialize">Reset</v-btn>
    </template>
  </v-data-table>
</template>

<script>
import io from "socket.io-client";
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
    this.refresh()
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
