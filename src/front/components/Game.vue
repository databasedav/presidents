<template>
  <v-container>
    <v-row dense>
      <v-col cols="12">
        <AlertSnackbar 
          :namespace="this.namespace"
        ></AlertSnackbar>
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12">
        <OtherPlayerBox
          :namespace="this.namespace"
        ></OtherPlayerBox>
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12">
        <InPlayBox
          :namespace="this.namespace"
        ></InPlayBox>
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12">
        <MessageBox
          :namespace="this.namespace"
        ></MessageBox>
      </v-col>
    </v-row>

    <v-row justify="center" dense>
      <v-col cols="9">
        <PlayerStrip
          :namespace="this.namespace"
          :spot="this.spot"
        ></PlayerStrip>
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12">
        <CardBox
          :namespace="this.namespace"
          @card_click="this.card_click"
        ></CardBox>
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12">
        <ButtonBox
          :namespace="this.namespace"
          @unlock="this.unlock"
          @lock="this.lock"
          @play="this.play"
          @unlock_pass="this.unlock_pass"
          @pass="this.pass"
          @ask="this.ask"
          @give="this.give"
          @asking_click="this.asking_click"
        ></ButtonBox>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import CardBox from "./CardBox.vue";
import ButtonBox from "./ButtonBox.vue";
import InPlayBox from "./InPlayBox.vue";
import AlertSnackbar from "./AlertSnackbar.vue";
import MessageBox from "./MessageBox.vue";
import PlayerStrip from "./PlayerStrip.vue";
import OtherPlayerBox from "./OtherPlayerBox.vue";
// import StoredHandBox from './StoredHandBox.vue'

import { create_server_module, EVENTS } from "../utils";

import io from "socket.io-client";

export default {
  name: "Game",

  components: {
    CardBox,
    ButtonBox,
    InPlayBox,
    AlertSnackbar,
    MessageBox,
    PlayerStrip,
    OtherPlayerBox
    // StoredHandBox
  },

  props: {
    game_id: null,
    // when true, plugs in testing socket and vuex module whose namespaces
    // are the id of the socket instead of the server namespace
    testing: {
      type: Boolean,
      default: false
    },
    testing_sid_index: Number
  },

  data () {
    return {
      sid: null
    };
  },

  watch: {
    game_id: {
      handler: function (game_id) {
        if (game_id) {
          this.$store.dispatch('join_game', {game_id: game_id, testing: this.testing})
        }
      },
      immediate: true
    }
  },

  methods: {
    card_click (card) {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'card_click',
        card: card
      })
    },

    unlock () {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'unlock'
      });
    },

    lock () {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'lock'
      });
    },

    play () {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'play'
      });
    },

    unlock_pass () {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'unlock_pass'
      });
    },

    pass () {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'pass'
      });
    },

    ask () {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'ask'
      });
    },

    give () {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'give'
      });
    },

    asking_click (rank) {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'asking_click',
        rank: rank
      });
    }
  },

  computed: {
    namespace () {
      return (this.testing && this.$store.state.testing_sids[this.testing_sid_index-1]) || this.game_id;
    },

    on_turn () {
      return this.$store.state[this.namespace].on_turn;
    },

    spot () {
      return this.$store.state[this.namespace].spot;
    }
  }
};
</script>
