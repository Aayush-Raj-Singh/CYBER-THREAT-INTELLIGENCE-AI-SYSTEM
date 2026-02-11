import { createContext, useContext, useMemo, useState } from "react";

import { cn } from "../../lib/utils";



const TabsContext = createContext(null);



function useTabsContext() {

  const context = useContext(TabsContext);

  if (!context) {

    throw new Error("Tabs components must be used within <Tabs>");

  }

  return context;

}



export function Tabs({ defaultValue, value, onValueChange, className, children }) {

  const [internalValue, setInternalValue] = useState(defaultValue);

  const currentValue = value ?? internalValue;



  const setValue = (nextValue) => {

    if (!nextValue || nextValue === currentValue) return;

    if (onValueChange) onValueChange(nextValue);

    if (value === undefined) setInternalValue(nextValue);

  };



  const contextValue = useMemo(

    () => ({ value: currentValue, setValue }),

    [currentValue]

  );



  return (

    <TabsContext.Provider value={contextValue}>

      <div className={cn("w-full", className)}>{children}</div>

    </TabsContext.Provider>

  );

}



export function TabsList({ className, ...props }) {

  return (

    <div

      role="tablist"

      className={cn(

        `

        w-full flex flex-nowrap sm:flex-wrap gap-1.5 sm:gap-2 overflow-x-auto sm:overflow-visible no-scrollbar

        rounded-2xl

        border border-slate-200/70

        bg-white/70

        p-1.5 sm:p-2

        backdrop-blur

        shadow-sm

        dark:border-slate-700/60

        dark:bg-slate-900/60

        `,

        className

      )}

      {...props}

    />

  );

}



export function TabsTrigger({ value, className, children, ...props }) {

  const { value: currentValue, setValue } = useTabsContext();

  const isActive = currentValue === value;



  return (

    <button

      type="button"

      role="tab"

      aria-selected={isActive}

      data-state={isActive ? "active" : "inactive"}

      onClick={() => setValue(value)}

      className={cn(

        `

        inline-flex items-center gap-2

        shrink-0 whitespace-nowrap

        rounded-xl

        px-3 py-1.5

        text-xs font-medium

        transition

        focus:outline-none

        sm:px-4 sm:py-2 sm:text-sm

        `,

        isActive

          ? `

            bg-white

            text-slate-900

            shadow-sm

            dark:bg-slate-800

            dark:text-slate-100

          `

          : `

            text-slate-600

            hover:bg-white/80

            hover:text-slate-900

            dark:text-slate-400

            dark:hover:bg-slate-800/60

            dark:hover:text-slate-100

          `,

        className

      )}

      {...props}

    >

      {children}

    </button>

  );

}



export function TabsContent({ value, className, ...props }) {

  const { value: currentValue } = useTabsContext();

  const isActive = currentValue === value;



  return (

    <div

      role="tabpanel"

      hidden={!isActive}

      data-state={isActive ? "active" : "inactive"}

      className={cn(

        "mt-6 focus:outline-none",

        isActive ? "block" : "hidden",

        className

      )}

      {...props}

    />

  );

}

