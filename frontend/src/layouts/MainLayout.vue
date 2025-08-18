<template>
  <q-layout view="hHh lpR fFf">

    <!-- HEADER BAR SHOWN ON ALL ROUTES -->
    <q-header elevated>
      <q-toolbar>
        <q-btn flat dense round icon="menu" @click="leftDrawer = !leftDrawer" />
        <q-toolbar-title>My Dashboard</q-toolbar-title>
        <q-btn flat label="SIGN UP" @click="showSignUp = true" />
        <q-btn flat label="SIGN IN" @click="showSignIn = true" />
      </q-toolbar>
    </q-header>

    <!-- MAIN CONTENT -->
    <q-page-container>
      <router-view />
    </q-page-container>

    <!-- SIGN UP DIALOG -->
    <q-dialog v-model="showSignUp">
      <q-card style="min-width: 400px">
        <q-card-section><div class="text-h6">Create an Account</div></q-card-section>
        <q-card-section>
          <q-input filled v-model="signUpForm.email" label="Email" />
          <q-input filled v-model="signUpForm.password" label="Password" type="password" />
          <q-input filled v-model="signUpForm.confirm" label="Confirm Password" type="password" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn label="Sign Up" color="primary" @click="submitSignUp" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- SIGN IN DIALOG -->
    <q-dialog v-model="showSignIn">
      <q-card style="min-width: 400px">
        <q-card-section><div class="text-h6">Sign In</div></q-card-section>
        <q-card-section>
          <q-input filled v-model="signInForm.email" label="Email" />
          <q-input filled v-model="signInForm.password" label="Password" type="password" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn label="Sign In" color="primary" @click="submitSignIn" />
        </q-card-actions>
      </q-card>
    </q-dialog>

  </q-layout>
</template>

<script>
  export default {
    name: 'MainLayout',
    data() {
      return {
        leftDrawer: false,
        showSignUp: false,
        showSignIn: false,
        signUpForm: {
          email: '',
          password: '',
          confirm: ''
        },
        signInForm: {
          email: '',
          password: ''
        }
      }
    },
    methods: {
      submitSignUp() {
        if (this.signUpForm.password !== this.signUpForm.confirm) {
          this.$q.notify({ type: 'negative', message: 'Passwords do not match' });
          return;
        }
        this.$q.notify({ type: 'positive', message: 'Signed up successfully!' });
        this.showSignUp = false;
      },
      submitSignIn() {
        this.$q.notify({ type: 'positive', message: 'Signed in successfully!' });
        this.showSignIn = false;
      }
    }
  }
</script>
