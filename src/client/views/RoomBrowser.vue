<template>
  <div>
  <v-toolbar flat color="white">
    <v-toolbar-title class='logo'>presidents</v-toolbar-title>
    <v-divider
      class="mx-2"
      inset
      vertical
    ></v-divider>
    <v-spacer></v-spacer>
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
                <v-text-field v-model="edited_room.name" label="room name"></v-text-field>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="blue darken-1" flat @click="close">Cancel</v-btn>
          <v-btn color="blue darken-1" flat @click="save">Save</v-btn>
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
      <td>{{ props.item.name }}</td>
      <td class="text-xs-center">{{ props.item.num_players }}</td>
      
      <td class="justify-center layout px-0">
        <v-btn
          color='success'
          :disabled='props.item.num_players === 4'
        >
          join room
        </v-btn>
      </td>
    </template>
  </v-data-table>
</div>
</template>

<script>
export default {
  data: () => ({
    dialog: false,
    headers: [
      {
        text: 'room name',
        align: 'left',
        sortable: false,
        value: 'name'
      },
      { text: '# players', value: 'num_players' },
      { text: 'actions', value: 'name', sortable: false }
    ],
    rooms: [],
    editedIndex: -1,
    editedItem: {
      name: ''
    },
    default_room: {
      name: ''
    }
  }),

  watch: {
    dialog (val) {
      val || this.close()
    }
  },

  created () {
    this.initialize()
  },

  methods: {
    initialize () {
      this.rooms = [
        {
          name: 'fuck',
          num_players: 4
        },
        {
          name: 'shit',
          num_players: 2
        },
      ]
    },

    close () {
      this.dialog = false
      setTimeout(() => {
        this.edited_room = Object.assign({}, this.default_room)
        this.editedIndex = -1
      }, 300)
    },

    save () {
      if (this.editedIndex > -1) {
        Object.assign(this.rooms[this.editedIndex], this.edited_room)
      } else {
        this.rooms.push(this.editedItem)
      }
      this.close()
    }
  }
}
</script>

<style>
.logo {
  color: black;
  font-family: 'Pacifico', cursive;
  font-size: 25pt
}
</style>
