import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {createStackNavigator} from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialIcons';

import Dashboard from './screens/Dashboard';
import Servers from './screens/Servers';
import ServerDetail from './screens/ServerDetail';
import Alerts from './screens/Alerts';
import Login from './screens/Login';
import {AuthProvider, useAuth} from './utils/AuthContext';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

const MainTabs = () => {
  const ServersStack = createStackNavigator();

  const ServersStackScreen = () => (
    <ServersStack.Navigator>
      <ServersStack.Screen
        name="ServersList"
        component={Servers}
        options={{headerShown: false}}
      />
      <ServersStack.Screen
        name="ServerDetail"
        component={ServerDetail}
        options={{title: 'Server Detail'}}
      />
    </ServersStack.Navigator>
  );

  return (
    <Tab.Navigator
      screenOptions={({route}) => ({
        tabBarIcon: ({focused, color, size}) => {
          let iconName;

          if (route.name === 'Dashboard') {
            iconName = 'dashboard';
          } else if (route.name === 'Servers') {
            iconName = 'dns';
          } else if (route.name === 'Alerts') {
            iconName = 'notifications';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#2196F3',
        tabBarInactiveTintColor: 'gray',
        headerShown: false,
      })}>
      <Tab.Screen name="Dashboard" component={Dashboard} />
      <Tab.Screen name="Servers" component={ServersStackScreen} />
      <Tab.Screen name="Alerts" component={Alerts} />
    </Tab.Navigator>
  );
};

const AppNavigator = () => {
  const {user, loading} = useAuth();

  if (loading) {
    return null; // You could add a loading screen here
  }

  return (
    <Stack.Navigator screenOptions={{headerShown: false}}>
      {user ? (
        <Stack.Screen name="Main" component={MainTabs} />
      ) : (
        <Stack.Screen name="Login" component={Login} />
      )}
    </Stack.Navigator>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <NavigationContainer>
        <AppNavigator />
      </NavigationContainer>
    </AuthProvider>
  );
};

export default App;
