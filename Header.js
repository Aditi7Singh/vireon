import { Flex, Text, Metric } from '@tremor/react';
import { ViewGridIcon } from '@heroicons/react/solid';

function VireonLogo() {
  // Replace with your actual SVG logo for Vireon
  return (
    <Flex alignItems="center" className="gap-2">
      <svg height="32" width="32" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="#1E40AF" />
        <text x="50%" y="50%" textAnchor="middle" dy=".3em" fill="white" fontSize="40" fontFamily="Arial, sans-serif">V</text>
      </svg>
      <Metric className="hidden sm:block">Vireon</Metric>
    </Flex>
  );
}

export default function Header() {
  return (
    <header className="p-4 border-b bg-white">
      <Flex justifyContent="between" alignItems="center">
        <VireonLogo />
        <Text>AI Financial Copilot</Text>
        {/* Add User Profile / Settings button here */}
      </Flex>
    </header>
  );
}

