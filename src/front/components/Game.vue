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
    // server namespace; also vuex module namespace when not testing
    server: String,
    // when true, plugs in testing socket and vuex module whose namespaces
    // are the id of the socket instead of the server namespace
    testing: {
      type: Boolean,
      default: false
    }
  },

  data () {
    return {
      sid: null
    };
  },

  created () {
    const socket = io(`http://127.0.0.1:5000${this.server}`, {
      forceNew: true,
      transportOptions: {
        polling: {
          extraHeaders: {
            'key': 'peepeepoopoo'
          }
        }
      }
    });

    socket.once("connect", () => {
      // if testing (i.e. four player vue), use socket's engine id (client's sid)
      // as namespace; otherwise uses the server namespace as individual
      // players (sockets) can be in a single game at most once; this is
      // here because need to wait till socket connects to get its id (sid)
      const namespace = this.testing ? socket.io.engine.id : this.server;
      this.$store.registerModule(namespace, create_server_module());
      // register presidents event listeners
      EVENTS.forEach(event => {
        socket.on(event, payload => {
          this.$store.commit(`${namespace}/${event}`, payload);
        });
      });
      // gives store access to namespaced socket
      this.$store.commit(`${namespace}/set_socket`, { socket: socket });
      this.sid = namespace;
    });
  },

  methods: {
    card_click (card) {
      this.$store.dispatch(`${this.namespace}/emit_card_click`, {
        card: card
      });
    },

    unlock () {
      this.$store.dispatch(`${this.namespace}/emit_unlock`);
    },

    lock () {
      this.$store.dispatch(`${this.namespace}/emit_lock`);
    },

    play () {
      this.$store.dispatch(`${this.namespace}/emit_play`);
    },

    unlock_pass () {
      this.$store.dispatch(`${this.namespace}/emit_unlock_pass`);
    },

    pass () {
      this.$store.dispatch(`${this.namespace}/emit_pass`);
    },

    ask () {
      this.$store.dispatch(`${this.namespace}/emit_ask`);
    },

    give () {
      this.$store.dispatch(`${this.namespace}/emit_give`);
    },

    asking_click (rank) {
      this.$store.dispatch(`${this.namespace}/emit_asking_click`, {
        rank: rank
      });
    }
  },

  computed: {
    namespace () {
      return (this.testing && this.sid) || this.server;
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
